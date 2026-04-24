import type {
  DesignScheme,
  DesignSchemeVersion,
  ModelSnapshot,
  Product,
  Project,
} from '@/api/engineering'

export type EngineeringTreeNodeType = 'project' | 'product' | 'scheme'

export type EngineeringTreeNodeData =
  | Project
  | (Product & { project_name?: string })
  | (DesignScheme & { product_name?: string; project_id?: number })

export interface EngineeringTreeNode {
  id: number
  key: string
  label: string
  type: EngineeringTreeNodeType
  data: EngineeringTreeNodeData
  children?: EngineeringTreeNode[]
}

export interface EngineeringStructureIndex {
  projectsById: Map<number, Project>
  productsById: Map<number, Product>
  schemesById: Map<number, DesignScheme>
  versionsById: Map<number, DesignSchemeVersion>
}

export interface SnapshotScopeRelation {
  projectId: number | null
  productId: number | null
  schemeId: number | null
  versionId: number
}

export function buildEngineeringStructureTree(
  projects: Project[],
  products: Product[],
  schemes: DesignScheme[],
): EngineeringTreeNode[] {
  const projectMap = new Map<number, EngineeringTreeNode>()

  const tree = projects.map((project) => {
    const node: EngineeringTreeNode = {
      id: project.id,
      key: `project-${project.id}`,
      label: project.name,
      type: 'project',
      data: project,
      children: [],
    }
    projectMap.set(project.id, node)
    return node
  })

  const productNodeMap = new Map<number, EngineeringTreeNode>()
  for (const product of products) {
    const projectNode = projectMap.get(product.project_id)
    if (!projectNode) {
      continue
    }

    const productNode: EngineeringTreeNode = {
      id: product.id,
      key: `product-${product.id}`,
      label: product.name,
      type: 'product',
      data: {
        ...product,
        project_name: projectNode.label,
      },
      children: [],
    }

    projectNode.children!.push(productNode)
    productNodeMap.set(product.id, productNode)
  }

  for (const scheme of schemes) {
    const productNode = productNodeMap.get(scheme.product_id)
    if (!productNode) {
      continue
    }

    const productData = productNode.data as Product & { project_name?: string }
    productNode.children!.push({
      id: scheme.id,
      key: `scheme-${scheme.id}`,
      label: scheme.name,
      type: 'scheme',
      data: {
        ...scheme,
        product_name: productNode.label,
        project_id: productData.project_id,
      },
    })
  }

  return tree
}

export function createEngineeringStructureIndex(
  projects: Project[],
  products: Product[],
  schemes: DesignScheme[],
  versions: DesignSchemeVersion[],
): EngineeringStructureIndex {
  return {
    projectsById: new Map(projects.map((item) => [item.id, item])),
    productsById: new Map(products.map((item) => [item.id, item])),
    schemesById: new Map(schemes.map((item) => [item.id, item])),
    versionsById: new Map(versions.map((item) => [item.id, item])),
  }
}

export function resolveSnapshotScopeRelation(
  snapshot: ModelSnapshot,
  index: EngineeringStructureIndex,
): SnapshotScopeRelation {
  const version = index.versionsById.get(snapshot.scheme_version_id)
  const scheme = version ? index.schemesById.get(version.scheme_id) ?? null : null
  const product = scheme ? index.productsById.get(scheme.product_id) ?? null : null

  return {
    projectId: product?.project_id ?? null,
    productId: product?.id ?? null,
    schemeId: scheme?.id ?? null,
    versionId: snapshot.scheme_version_id,
  }
}

export function matchesTreeNodeScope(
  relation: SnapshotScopeRelation,
  node: EngineeringTreeNode | null,
): boolean {
  if (!node) {
    return true
  }

  if (node.type === 'project') {
    return relation.projectId === node.id
  }

  if (node.type === 'product') {
    return relation.productId === node.id
  }

  return relation.schemeId === node.id
}